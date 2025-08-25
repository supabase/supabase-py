from storage3.exceptions import StorageApiError


def test_storage_api_error_initialization():
    # Arrange
    message = "Test error message"
    code = "TEST_ERROR"
    status = 400

    # Act
    error = StorageApiError(message, code, status)

    # Assert
    assert error.message == message
    assert error.code == code
    assert error.status == status
    assert error.name == "StorageApiError"
    assert (
        str(error)
        == "{'statusCode': 400, 'error': TEST_ERROR, 'message': Test error message}"
    )


def test_storage_api_error_to_dict():
    # Arrange
    error = StorageApiError("Test message", "TEST_CODE", 404)

    # Act
    error_dict = error.to_dict()

    # Assert
    assert error_dict == {
        "name": "StorageApiError",
        "code": "TEST_CODE",
        "message": "Test message",
        "status": 404,
    }


def test_storage_api_error_inheritance():
    # Arrange & Act
    error = StorageApiError("Test message", "TEST_CODE", 500)

    # Assert
    from storage3.utils import StorageException

    assert isinstance(error, StorageException)
