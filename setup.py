from distutils.core import setup

long_description = open('README').read()

setup(
    name='django-layar',
    version="0.1.0",
    package_dir={'layar': 'layar'},
    packages=['layar'],
    description='helper for publishing data to Layar augmented reality browser from Django',
    author='James Turk',
    author_email='jturk@sunlightfoundation.com',
    license='BSD License',
    url='http://github.com/sunlightlabs/django-layar/',
    long_description=long_description,
    platforms=["any"],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Environment :: Web Environment',
    ],
)
