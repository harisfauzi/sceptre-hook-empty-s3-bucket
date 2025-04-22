from setuptools import setup, find_packages

install_requirements = [
    "sceptre>=4.5.0",
]

setup(
    name="sceptre_hook_empty_s3_bucket",
    version="1.0.0",
    description="A Sceptre hook to empty an S3 bucket.",
    py_modules=["hooks.empty_bucket"],
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    entry_points={
        "sceptre.hooks": [
            "sceptre_empty_s3_bucket = hooks.empty_bucket:EmptyBucketHook",
        ],
    },
    install_requires=install_requirements,
)
