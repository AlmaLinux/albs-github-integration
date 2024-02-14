from setuptools import setup

setup(
    name='albs_github',
    version='0.1.1',
    author='Vasily Kleschov',
    author_email='kleshev12@gmail.com',
    description=(
        'The wrapper around GitHub GraphQL API focused on integration '
        'with projects'
    ),
    url='https://github.com/AlmaLinux/albs-github-integration',
    project_urls={
        'Bug Tracker': 'https://github.com/AlmaLinux/albs-github-integration/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: '
        'GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
    ],
    packages=['albs_github', 'albs_github/graphql'],
    install_requires=[
        'aiohttp>=3.8.6',
        'jmespath>=1.0.1',
        'pydantic>=2.4.2',
        'requests>=2.26.0',
    ],
    python_requires='>=3.7',
)
