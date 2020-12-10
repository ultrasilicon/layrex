from setuptools import setup, find_packages


setup(name="layrex",
      version="0.0.1",
      author="Tim Zheng",
      author_email="zhenghanecho@gmail.com",
      description=("Binary behavior collection sandbox tool"),
      license="GPLv3",
      url="https://github.com/ultrasilicon/",
      packages=find_packages(where='src'),
      package_dir={'': 'src'},
      classifiers=[
          "Topic :: Utilities",
      ],
      install_requires=[
          'typer',
          'docker',
          'mdutils'
      ],
      entry_points={
          'console_scripts': [
              'layrex = layrex.app:main',
          ],
      })
