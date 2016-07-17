import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = ('Arche',
            'betahaus.viewcomponent',
            'pyramid',
            'pyramid_chameleon',)


setup(name='arche_papergirl',
      version='0.1dev',
      description='Newsletter composter for Arche',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='Arche dev team and contributors',
      author_email='robin@betahaus.net',
      url='https://github.com/ArcheProject',
      keywords='web pyramid pylons arche',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="arche_papergirl",
      entry_points = """\
      [fanstatic.libraries]
      arche_papergirl = arche_papergirl.fanstatic_lib:papergirl_lib
      """,
      )
