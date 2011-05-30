from setuptools import setup, find_packages

version = '0.2'

setup(
    name='django-bop',

    version=version,
    description="Basic Object-level Permissions in django (1.2+)",
    long_description=open('README.rst').read(),
    keywords='django object level permissions',
    author='Peter van Kampen',
    author_email='pterk@datatailors.com',
    url='',
    license='BSD',
    packages=find_packages(),
    # namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
)
