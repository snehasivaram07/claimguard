import hashlib
import io
from unittest.mock import MagicMock

import pytest

from app.storage.storage_service import (
    HashingStreamWrapper,
    StorageService,
)


def test_sanitize_filename_prevents_path_traversal():
    assert StorageService.sanitize_filename("../../etc/passwd") == "passwd"
    assert StorageService.sanitize_filename(r"..\..\windows\system32\calc.exe") == "calc.exe"
    assert StorageService.sanitize_filename("my claim document.pdf") == "my_claim_document.pdf"
    assert StorageService.sanitize_filename("valid_report-v1.2.pdf") == "valid_report-v1.2.pdf"
    assert StorageService.sanitize_filename("...") == "unnamed_document"
    assert StorageService.sanitize_filename("") == "unnamed_document"


def test_build_object_key_namespacing():
    key = StorageService.build_object_key(
        owner_id="usr-123",
        claim_id="clm-456",
        document_id="doc-789",
        original_filename="../../dangerous-name.pdf",
    )
    assert key == "usr-123/clm-456/doc-789/dangerous-name.pdf"


def test_hashing_stream_wrapper_computes_exact_sha256():
    payload = b"Antigravity ClaimGuard Secure Document Stream 1234567890"
    expected_hash = hashlib.sha256(payload).hexdigest()

    raw_stream = io.BytesIO(payload)
    wrapped = HashingStreamWrapper(raw_stream)

    # Read in chunks
    chunks = []
    while True:
        chunk = wrapped.read(16)
        if not chunk:
            break
        chunks.append(chunk)

    reconstructed = b"".join(chunks)
    assert reconstructed == payload
    assert wrapped.bytes_read == len(payload)
    assert wrapped.hexdigest == expected_hash


def test_hashing_stream_wrapper_enforces_max_size():
    payload = b"Exceeding byte limits test data"
    raw_stream = io.BytesIO(payload)
    wrapped = HashingStreamWrapper(raw_stream, max_size_bytes=10)

    with pytest.raises(ValueError, match="exceeds maximum allowed size"):
        wrapped.read(20)


def test_put_object_stream_delegates_to_s3():
    mock_s3 = MagicMock()
    # Simulate boto3 consuming the file stream
    mock_s3.upload_fileobj.side_effect = lambda Fileobj, **_kwargs: Fileobj.read()
    service = StorageService(client=mock_s3, bucket_name="test-bucket")

    payload = b"Hello MinIO / S3"
    stream = io.BytesIO(payload)
    expected_hash = hashlib.sha256(payload).hexdigest()

    result = service.put_object_stream(
        stream=stream,
        object_key="owner/claim/doc/file.pdf",
        content_type="application/pdf",
    )

    assert result["object_key"] == "owner/claim/doc/file.pdf"
    assert result["content_hash"] == expected_hash
    assert result["size_bytes"] == len(payload)

    # Verify boto3 upload_fileobj was called
    mock_s3.upload_fileobj.assert_called_once()
    call_kwargs = mock_s3.upload_fileobj.call_args[1]
    assert call_kwargs["Bucket"] == "test-bucket"
    assert call_kwargs["Key"] == "owner/claim/doc/file.pdf"
    assert call_kwargs["ExtraArgs"]["ContentType"] == "application/pdf"


def test_generate_presigned_download_url():
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = "https://s3.local/test-bucket/key?signature=xyz"
    service = StorageService(client=mock_s3, bucket_name="test-bucket")

    url = service.generate_presigned_download_url(
        object_key="owner/claim/doc/report.pdf",
        original_filename="Original Report.pdf",
        expires_in=300,
    )

    assert "https://" in url
    mock_s3.generate_presigned_url.assert_called_once_with(
        ClientMethod="get_object",
        Params={
            "Bucket": "test-bucket",
            "Key": "owner/claim/doc/report.pdf",
            "ResponseContentDisposition": 'attachment; filename="Original_Report.pdf"',
        },
        ExpiresIn=300,
    )


def test_delete_object():
    mock_s3 = MagicMock()
    service = StorageService(client=mock_s3, bucket_name="test-bucket")

    success = service.delete_object(object_key="owner/claim/doc/file.pdf")
    assert success is True
    mock_s3.delete_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="owner/claim/doc/file.pdf",
    )
