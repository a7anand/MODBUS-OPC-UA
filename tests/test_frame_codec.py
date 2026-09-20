from app.modbus.frame_codec import read_exchange_hex, read_request_pdu


def test_read_request_pdu():
    assert read_request_pdu(1, 3, 0, 2) == "01 03 00 00 00 02"


def test_read_exchange_ok():
    tx, rx = read_exchange_hex(1, 3, 0, 1, [100], True)
    assert tx == "01 03 00 00 00 01"
    assert "01 03 02" in rx
