from setuptools import setup, find_packages

setup(
    name="getpaid.io",
    version="0.2.0",
    packages=find_packages('src'),
    package_dir={'':'src'},
    namespace_packages=['getpaid'],
    include_package_data=True,
    install_requires = [ 'setuptools',
                         'getpaid.core' 
                         ],
    zip_safe = False,
    )
