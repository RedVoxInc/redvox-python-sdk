from redvox.common import data_window_wpa as dwpa


def main():
    path = "/Users/yusukehatanaka/Desktop/DATA/20201006_SPX_F9"
    save_path = "/Users/yusukehatanaka/Desktop/DATA/issue_360/"

    dw_config = dwpa.DataWindowConfigWpa(
        input_dir=path
    )

    drws = dwpa.DataWindowArrow(
        "single_station_no_save",
        config=dw_config,
        out_dir=save_path,
        out_type="PARQUET"
    )

    print(f"start_dt: {int(drws.get_start_date())}")
    print(f"end_dt  : {int(drws.get_end_date())}")

    drws.save()


if __name__ == '__main__':
    main()
