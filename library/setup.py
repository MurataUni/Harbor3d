from setuptools import setup, find_packages

setup(
    name='harbor3d',
    version="0.2.5",
    description="STL形式のファイルを出力可能な3Dモデリングツール",
    long_description="STL形式のファイルを出力可能な3Dモデリングツール\nコーディングで3Dモデルを作成する",
    url='',
    author='Murata Uni',
    author_email='',
    license='Apache License, Version 2.0',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Manufacturing",
        "License :: Apache License, Version 2.0",
        "Programming Language :: Python :: 3.7",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
    ],
    keywords='3D Modeling',
    install_requires=["numpy"],
    packages=find_packages(exclude=('demo', 'docs')),
)
