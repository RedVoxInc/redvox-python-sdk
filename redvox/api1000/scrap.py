import redvox.api1000.wrapped_packet as w
import redvox.api1000.microphone_channel as microphone_chanel
import redvox.api1000.proto.redvox_api_1000_pb2 as p
import numpy as np

def main():
    m = microphone_chanel.MicrophoneChannel.new()
    print(m)
    m.get_samples().append_sample(1, True).append_sample(2, True)
    print(m)
    print(type(m.get_proto().SerializeToString()))




if __name__ == "__main__":
    main()
