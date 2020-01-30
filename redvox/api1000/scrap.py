import redvox.api1000.wrapped_packet as w


def main():
    s = w.SummaryStatistics.new()
    s.update_from_values([1, 2, 3, 4, 5])
    print("stats", s)


if __name__ == "__main__":
    main()
