from distutils.core import setup
setup(
  name = 'async_test_suite',         # How you named your package folder (MyLib)
  packages = ['async_test_suite'],   # Chose the same as "name"
  version = '0.1',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'An extension to unittest suites to work in parallel',   # Give a short description about your library
  author = 'Yuval Ezuz',                   # Type in your name
  author_email = 'uv.ezuz@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/yuvalez/async_test_suite',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/yuvalez/async_test_suite/archive/v_01.tar.gz',    # I explain this later on
  keywords = ['ASYNC', 'TESTS'],   # Keywords that define your package best
  install_requires=['asynctest'],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
  ],
)