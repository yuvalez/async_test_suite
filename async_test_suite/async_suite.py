import asyncio
import inspect
import unittest
from unittest import TestResult

import asynctest


class AsyncTestCase(asynctest.TestCase):

    def run(self, result=None):
        orig_result = result
        if result is None:
            result = self.defaultTestResult()
            startTestRun = getattr(result, 'startTestRun', None)
            if startTestRun is not None:
                startTestRun()

        result.startTest(self)

        testMethod = getattr(self, self._testMethodName)
        if (getattr(self.__class__, "__unittest_skip__", False) or
                getattr(testMethod, "__unittest_skip__", False)):
            # If the class or method was skipped.
            try:
                skip_why = (getattr(self.__class__, '__unittest_skip_why__', '') or
                            getattr(testMethod, '__unittest_skip_why__', ''))
                self._addSkip(result, self, skip_why)
            finally:
                result.stopTest(self)
            return
        expecting_failure = getattr(testMethod,
                                    "__unittest_expecting_failure__", False)
        outcome = unittest.case._Outcome(result)
        try:
            self._outcome = outcome

            with outcome.testPartExecutor(self):
                self._setUp()
            if outcome.success:
                outcome.expecting_failure = expecting_failure
                with outcome.testPartExecutor(self, isTest=True):
                    self._run_test_method(testMethod)
                outcome.expecting_failure = False
                with outcome.testPartExecutor(self):
                    self._tearDown()

            self.loop.run_until_complete(self.doCleanups())
            for test, reason in outcome.skipped:
                self._addSkip(result, test, reason)
            self._feedErrorsToResult(result, outcome.errors)
            if outcome.success:
                if expecting_failure:
                    if outcome.expectedFailure:
                        self._addExpectedFailure(result, outcome.expectedFailure)
                    else:
                        self._addUnexpectedSuccess(result)
                else:
                    result.addSuccess(self)
            return result
        finally:
            result.stopTest(self)
            if orig_result is None:
                stopTestRun = getattr(result, 'stopTestRun', None)
                if stopTestRun is not None:
                    stopTestRun()

            # explicitly break reference cycles:
            # outcome.errors -> frame -> outcome -> outcome.errors
            # outcome.expectedFailure -> frame -> outcome -> outcome.expectedFailure
            outcome.errors.clear()
            outcome.expectedFailure = None

            # clear the outcome, no more needed
            self._outcome = None

    def _tearDown(self):
        if asyncio.iscoroutinefunction(self.tearDown):
            self.loop.run_until_complete(self.tearDown())
        else:
            self.tearDown()

        # self._unset_loop()
        # post-test checks
        self._checker.check_test(self)


class AsyncTestSuite(asynctest.TestSuite):

    def __init__(self):
        super(AsyncTestSuite, self).__init__()

        self.preview_classes = list()

    async def handleClassSetUp(self, test, result):
        # Checking if we already made a setup for this class.
        previousClass = getattr(result, '_previousTestClass', None)
        if previousClass is not None and previousClass not in self.preview_classes:
            self.preview_classes.append(previousClass)
        currentClass = test.__class__
        if currentClass in self.preview_classes:
            return
        if result._moduleSetUpFailed:
            return
        if getattr(currentClass, "__unittest_skip__", False):
            return

        try:
            currentClass._classSetupFailed = False
        except TypeError:
            # test may actually be a function
            # so its class will be a builtin-type
            pass

        setUpClass = getattr(currentClass, 'setUpClass', None)
        if setUpClass is not None:
            # _call_if_exists implementation
            func = getattr(result, '_setupStdout', lambda: None)
            func()
            try:
                if inspect.iscoroutinefunction(setUpClass):
                    self.preview_classes.append(currentClass)
                    await setUpClass()
                else:
                    setUpClass()
                    self.preview_classes.append(currentClass)

            except Exception as e:
                currentClass._classSetupFailed = True
                className = currentClass.__class__
                errorName = 'setUpClass (%s)' % className
                self._addClassOrModuleLevelException(result, e, errorName)
            finally:
                # _call_if_exists implementation
                func = getattr(result, '_restoreStdout', lambda: None)
                func()

    def run(self, result: TestResult) -> TestResult:
        top_level = False
        if getattr(result, '_testRunEntered', False) is False:
            result._testRunEntered = top_level = True
        async_method = list()
        # Generating a new event loop.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Add all async methods to the async methods list.
        for index, test in enumerate(self):
            async_method.append(self.startRunCase(index, test, result))
        # Run all methods in parallel.
        if async_method:
            loop.run_until_complete(asyncio.wait(async_method))
        loop.close()
        if top_level:
            self._tearDownPreviousClass(None, result)
            self._handleModuleTearDown(result)
            result._testRunEntered = False
        return result

    async def startRunCase(self, index, test, result):
        def _isnotsuite(test):
            try:
                iter(test)
            except TypeError:
                return True
            return False

        loop = asyncio.get_event_loop()
        if result.shouldStop:
            return False

        # Handle and teardown between modules.
        if _isnotsuite(test):
            self._tearDownPreviousClass(test, result)
            self._handleModuleFixture(test, result)
            await self.handleClassSetUp(test, result)
            result._previousTestClass = test.__class__
            self.preview_classes.append(test.__class__)

            if (getattr(test.__class__, '_classSetupFailed', False) or
                    getattr(result, '_moduleSetUpFailed', False)):
                return True

        await loop.run_in_executor(None, test, result)
        try:
            pass
        except AttributeError as e:
            print(str(e))

        if self._cleanup:
            self._removeTestAtIndex(index)
