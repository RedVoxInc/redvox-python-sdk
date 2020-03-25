# import api1000.common as common




import redvox.api900.reader as reader
import redvox.api1000.conversions as conversions
import redvox.api1000.wrapped_packet

def main():
    # data = reader.read_rdvxz_file_range("/Users/anthony/scrap/api900", redvox_ids=["1637610014"], structured_layout=True, concat_continuous_segments=False)
    # file = data["1637610014:415380355"][0]
    # file.write_rdvxz("/Users/anthony/scrap", "old.rdvxz")
    # file = conversions.convert_api900_to_api1000(file)
    # file.write_compressed_to_file("/Users/anthony/scrap", "new.rdvxz")
    # file.write_json_to_file("/Users/anthony/scrap", "new.json")
    data = redvox.api1000.wrapped_packet.WrappedRedvoxPacketApi1000.from_compressed_path("/Users/anthony/scrap/new.rdvxz")
    print(data)

if __name__ == "__main__":
    main()
