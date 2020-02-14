
yml = []

yml.append("""
name: Build wheels
on: [push]

jobs:
""")

# Mac & Windows builds
yml.append("""
  mac_windows:

    strategy:
      matrix:
        python-version: [2.7, 3.5, 3.6, 3.7, 3.8]
        platform: [macos-latest, windows-latest]
    runs-on: ${{ matrix.platform }}

    steps:
    - uses: actions/checkout@v2
    - uses: ilammy/msvc-dev-cmd@v1
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v1
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install Microsoft Visual C++ Compiler for Python 2.7
      if: (matrix.platform == 'windows-latest') && (matrix.python-version == '2.7')
      uses: crazy-max/ghaction-chocolatey@v1
      with:
        args: install vcpython27
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install setuptools wheel
    - name: Build
      run: |
        python setup.py bdist_wheel
    - name: Upload artifacts
      uses: actions/upload-artifact@v1
      with:
        name: build-${{ matrix.platform }}-${{ matrix.python-version }}
        path: dist
""")

# Python 2.7
yml.append("""
  linux-27:

    strategy:
      matrix:
        python-version: [2.7]

    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        python -m pip install setuptools wheel
    - name: Build
      run: |
        python setup.py bdist_wheel
    - name: Upload artifacts
      uses: actions/upload-artifact@v1
      with:
        name: build-manylinux-{pyver}
        path: dist
""")

# manylinuxes for 3.x
for pyver in ['35', '36', '37', '38']:
    # There seems to be no way (as of 2020-02-13) to accomplish this in the YAML
    # (unlike in Azure Pipelines)
    if pyver == '38':
        pycommand = '/opt/python/cp38-cp38/bin/python'
    else:
        pycommand = f'/opt/python/cp{pyver}-cp{pyver}m/bin/python'

    yml.append(f"""
  manylinux-{pyver}:

    runs-on: ubuntu-latest
    container: quay.io/pypa/manylinux2014_x86_64

    steps:
    - uses: actions/checkout@v2
    - name: Install dependencies
      run: |
        {pycommand} -m pip install --upgrade pip
        {pycommand} -m pip install setuptools wheel auditwheel
    - name: Build
      run: |
        {pycommand} setup.py bdist_wheel
    - name: Run auditwheel
      run: |
        mkdir dist/wheelhouse
        {pycommand} -m auditwheel repair -w dist/wheelhouse/ bindings/dist/*.whl
        rm dist/*.whl
        mv dist/wheelhouse/* bindings/dist/
        rm -rf dist/wheelhouse
    - name: Upload artifacts
      uses: actions/upload-artifact@v1
      with:
        name: build-manylinux-{pyver}
        path: dist
""")

# And finally, write the output file
with open('wheels.yml', 'w', encoding='utf-8') as f:
    f.write(''.join(yml))
