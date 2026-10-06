import subprocess
import platform
import os
import shutil
import glob
import tempfile

from dl_coursera import app_name, app_version


def _generate_self_signed_pfx(path, password):
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'dl_coursera')])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CODE_SIGNING]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    pfx = pkcs12.serialize_key_and_certificates(
        name=b'dl_coursera',
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(
            password.encode('utf-8')
        ),
    )
    with open(path, 'wb') as ofs:
        ofs.write(pfx)


def _find_signtool():
    signtool = shutil.which('signtool')
    if signtool:
        return signtool

    candidates = glob.glob(
        r'C:\Program Files (x86)\Windows Kits\10\bin\10.0.*\x64\signtool.exe'
    )
    if not candidates:
        raise FileNotFoundError('signtool.exe not found')
    return sorted(candidates)[-1]


def _sign_windows_executable(exe):
    password = 'changeit'
    pfx_fd, pfx_path = tempfile.mkstemp(suffix='.pfx')
    os.close(pfx_fd)

    try:
        _generate_self_signed_pfx(pfx_path, password)
        subprocess.run(
            [
                _find_signtool(),
                'sign',
                '/fd',
                'SHA256',
                '/f',
                pfx_path,
                '/p',
                password,
                '/tr',
                'http://timestamp.digicert.com',
                '/td',
                'SHA256',
                exe,
            ],
            check=True,
        )
    finally:
        os.unlink(pfx_path)


def main():
    outdir = f'{app_name}-{app_version}-nuitka-{platform.system()}-{platform.machine()}'
    exe = app_name
    if platform.system() == 'Windows':
        exe += '.exe'

    env = dict(os.environ)
    env['PYTHONPATH'] = os.getcwd()
    subprocess.run(
        f"""python -m nuitka
            --follow-imports --standalone --onefile --assume-yes-for-downloads
            --include-module=lxml.etree
            --include-package-data=dl_coursera.resource
            --output-dir=__data/{outdir}
            --output-filename={exe}
            dl_coursera_run.py""".split(),
        check=True,
        env=env,
    )

    os.chdir('__data')

    subprocess.run([os.path.join(outdir, exe), '--version'], check=True)
    subprocess.run([os.path.join(outdir, exe), '--help'], check=True)

    shutil.rmtree(os.path.join(outdir, 'dl_coursera_run.build'))
    shutil.rmtree(os.path.join(outdir, 'dl_coursera_run.dist'))
    shutil.rmtree(os.path.join(outdir, 'dl_coursera_run.onefile-build'))
    if platform.system() == 'Windows':
        _sign_windows_executable(os.path.join(outdir, exe))
    shutil.make_archive(
        base_name=outdir, format="zip", root_dir='.', base_dir=outdir, verbose=True
    )


if __name__ == '__main__':
    main()
