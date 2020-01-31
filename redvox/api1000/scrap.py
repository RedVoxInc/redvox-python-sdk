import redvox.api1000.wrapped_packet as w
import redvox.api1000.proto.redvox_api_1000_pb2 as p
import numpy as np

def main():
    wp = w.WrappedRedvoxPacketApi1000.new()
    print(wp.get_microphone_channel())




if __name__ == "__main__":
    main()
