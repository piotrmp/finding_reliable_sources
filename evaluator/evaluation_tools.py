def precision(actual, predicted, k):
    act_set = set(actual)
    # print("ACTUAL")
    # print(actual)
    pred_set = set(predicted[:k])
    
    # print("PREDICTED")
    # print(predicted[:k])
    result = len(act_set & pred_set) / float(k)
    return result


def remove_duplicates(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(
        x))]  # Note: seen.add() always returns None, so the "or" is there only as a way to attempt a set update
