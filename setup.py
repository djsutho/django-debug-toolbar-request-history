from setuptools import setup, find_packages

setup(
    name='django-debug-toolbar-request-history',
    version='0.0.1',
    description='Request History Panel for Django Debug Toolbar',
    author='David Sutherland',
    author_email='',
    license='BSD',
    packages=find_packages(exclude=('tests', 'example')),
    include_package_data=True,
    install_requires=['django-debug-toolbar'],
)