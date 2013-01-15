from distutils.core import setup

setup(
    name='hypernode-nodescripts',
    version='0.1',
    packages=['hypernode', 'hypernode.healthcheck', 'hypernode.nodeconfig'],
    scripts=['bin/check_mailout', 'bin/hypernode-apply-nodeconfig'],
    url='https://github.com/hypernode/nodescripts.git',
    license='',
    author='Allard Hoeve',
    author_email='allardhoeve@gmail.com',
    description=''
)
