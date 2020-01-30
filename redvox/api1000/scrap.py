import redvox.api1000.summary_statistics as w


def main():
    s = w.SummaryStatistics.new()
    s.set_count("foo")

    print(s.get_metadata())


if __name__ == "__main__":
    main()
