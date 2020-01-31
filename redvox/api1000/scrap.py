import redvox.api1000.summary_statistics as w
import numpy as np

def main():
    s = w.SummaryStatistics.new()
    s.update_from_values(np.array(["a", "b"]))
    print(s)
    # print(s.get_variance())




if __name__ == "__main__":
    main()
