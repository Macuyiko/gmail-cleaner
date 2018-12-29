from difflib import SequenceMatcher
from functools import lru_cache


def combine_strings(a, b, char='-', min_thres=3):
    s = SequenceMatcher()
    s.set_seq1(a)
    s.set_seq2(b)
    blocks = s.get_matching_blocks()
    combined = ''
    last_a, last_b = 0, 0
    for block in blocks:
        combined += char * max(block.a - last_a, block.b - last_b)
        last_a = block.a + block.size
        last_b = block.b + block.size
        piece_to_add = a[block.a:block.a+block.size]
        combined += piece_to_add if len(piece_to_add) > min_thres else char * len(piece_to_add)
    combined += char * (len(combined) - max(len(a), len(b)))
    return combined


def combine_clusters(clusters):
    representations = []
    for cluster in clusters:
        representation = cluster
        while len(representation) > 1:
            a = representation.pop()
            b = representation.pop()
            representation.append(combine_strings(a, b))
        representations.append(representation[0])
    return representations


@lru_cache(maxsize=1024)
def get_ratio(a, b):
    s = SequenceMatcher()
    s.set_seq1(a)
    s.set_seq2(b)
    return s.ratio() 


def find_best_match(clusters, ratio_threshold):
    s = SequenceMatcher()
    best_abval = (None, None, 0)
    for i in range(len(clusters) - 1):
        for j in range(i + 1, len(clusters)):
            r = min([get_ratio(a, b) for a in clusters[i] for b in clusters[j]])
            if r > best_abval[2] and r >= ratio_threshold:
                best_abval = (i, j, r)
    return best_abval
            

def cluster_strings(strings, ratio_threshold=0.6, combiner=combine_clusters, matcher=find_best_match):
    clusters = [[x] for x in strings]
    while len(clusters) > 1:
        best_abval = matcher(clusters, ratio_threshold)
        if best_abval[0] is None:
            break
        new_level = []
        for i in range(len(clusters)):
            if i == best_abval[0] or i == best_abval[1]:
                continue
            new_level.append(clusters[i])
        new_level.append(clusters[best_abval[0]] + clusters[best_abval[1]])
        clusters = new_level
    return combiner(clusters), clusters


if __name__ == '__main__':
    print('-------------------')

    strings = ["You have a message from Name Lastname waiting for 3 days",
               "You have a message from Jon Snow waiting for 393 days",
               "You have a message from Bob Bobbert waiting for 4 days",
               "You have a message from Marc Marcussen waiting for 1 day",
               "Jon Snow liked a photo of you",
               "Laurence Marcus liked a photo of you",
               "Aurelie liked a photo of you",
               "Jon Snow is waiting for your reply"]


    representations, clusters = cluster_strings(strings)

    for cluster in representations:
        #print('\n==============')
        print(cluster)
        #print('==> ')
        #print(cluster.members)
