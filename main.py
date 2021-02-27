import os
from datetime import datetime, timedelta
from timeit import default_timer as timer

DATA_FOLDER = './data/'
EDGES_URL = 'https://snap.stanford.edu/data/loc-gowalla_edges.txt.gz'
EDGES_COMP_FILE = 'loc-gowalla_edges.txt.gz'
EDGES_FILE = 'loc-gowalla_edges.txt'
CHECKINS_URL = 'https://snap.stanford.edu/data/loc-gowalla_totalCheckins.txt.gz'
CHECKINS_COMP_FILE = 'loc-gowalla_totalCheckins.txt.gz'
CHECKINS_FILE = 'loc-gowalla_totalCheckins.txt'
N_CHUNKS = 4

block_sizes = 0


class FriendshipGraph:
    """
    This class represents friendship associations between people
    """
    def __init__(self):
        """
        Constructor initializer
        """
        self.relations = {}

    def add_relation(self, user_id, friend_id):
        """
        Adds a friendship association between two people
        """
        if not self.relations.get(user_id):
            self.relations[user_id] = {friend_id}
        else:
            self.relations[user_id].add(friend_id)


class StalkingGraph:
    """
    This class represents stalking associations between people
    """
    def __init__(self):
        """
        Constructor initializer
        """
        self.weights = {}

    def add_weight(self, stalked_id, stalker_id, location_id):
        """
        Adds a location for a pair (stalked, stalker)
        """
        pair = stalked_id, stalker_id
        if not self.weights.get(pair):
            self.weights[pair] = {location_id}
        else:
            self.weights[pair].add(location_id)


def count_checkins_lines():
    """
    Returns the count of lines for the check-ins file
    """
    try:
        count = 0
        with open(f'{DATA_FOLDER}{CHECKINS_FILE}') as checkins:
            for line in checkins:
                count += 1
            return count
    except Exception as e:
        print('Problem counting lines for checkins file')
        print(e)
        return 0


def obtain_data_files(url):
    """
    Uses Linux/Unix commands to retrieve the file from the specified URL
    """
    try:
        os.system('echo "Downloading file...."')
        os.system(f'wget {url} -P {DATA_FOLDER}')
    except Exception as e:
        print('Problem retrieving files')
        print(e)


def extract_data_files(filename):
    """
    Uses Linux/Unix commands to extract the retrieved files
    """
    try:
        os.system(f'echo "Uncompressing {DATA_FOLDER}{filename}"')
        os.system(f'gzip -dkv {DATA_FOLDER}{filename}')
    except Exception as e:
        print(f'There was a problem when uncompressing the file {DATA_FOLDER}{filename}')
        print(e)


def read_friendship_graph(data_folder, friends_file):
    """
    Reads the edges (friendships) file and returns a graph with the associations
    """
    print('\tBuilding the Friendship Graph...')
    friendship_graph = FriendshipGraph()

    try:
        with open(f'{data_folder}{friends_file}') as edges:
            for line in edges:
                user, friend = line.split('\t')
                user = int(user)
                friend = int(friend.replace('\n', ''))
                friendship_graph.add_relation(user, friend)

        print('\tFinished building the Friendship Graph')
        return friendship_graph
    except Exception as e:
        print('Problem processing the friendships file')
        print(e)
        return None


def read_stalkers_graph(data_folder, checkins_file):
    """
    Reads the check-ins file and returns a graph with the associations between people
    that mean stalking (weighted as a list of involved location ids)

    Reading is performed with the chunking method for the specified buffer block size
    """
    print('\tBuilding the Stalkers Graph')
    stalkers_graph = StalkingGraph()
    visit_records = {}
    i = 1
    size_index = 0

    try:
        with open(f'{data_folder}{checkins_file}') as checkins:
            for line in checkins:

                if i % 50000 == 0:
                    print(f'\t\tProcessed {i} check-in records in chunk # {size_index + 1}')

                user_id, checkin_time, _, _, location_id = line.split('\t')
                user_id = int(user_id)
                checkin_time = checkin_time.replace('Z', '+00:00')
                location_id = int(location_id.replace('\n', ''))

                new_visit = (user_id, checkin_time)

                if not visit_records.get(location_id):
                    visit_records[location_id] = [new_visit]
                else:
                    for visit in visit_records[location_id]:
                        if new_visit[0] != visit[0]:
                            if new_visit[1] < visit[1]:
                                stalkers_graph.add_weight(new_visit[0], visit[0], location_id)
                            else:
                                stalkers_graph.add_weight(visit[0], new_visit[0], location_id)

                    visit_records[location_id].append(new_visit)

                if i == block_sizes[size_index]:
                    yield stalkers_graph
                    i = 1
                    size_index += 1
                else:
                    i += 1

            print('\tFinished building the Stalkers Graph')
            return stalkers_graph
    except Exception as e:
        print('Problem processing the checkins file')
        print(e)
        return None


def combine_graphs(left_graph, right_graph):
    """
    Returns the combination of the left and right graphs
    The left graph will store all in the right one
    """
    for pair in left_graph.weights:
        left_graph.weights[pair].update(right_graph.weights[pair])

    return left_graph


def obtain_stalkers_graph(data_folder, checkins_filename, edges_filename, graph_generator):
    """
    Returns the total Stalkers Graph as a combination of partial Stalker Graphs
    """
    final_stalkers_graph = None

    for graph in graph_generator:
        if not final_stalkers_graph:
            final_stalkers_graph = graph
        else:
            final_stalkers_graph = combine_graphs(final_stalkers_graph, graph)
            del(graph)
        print('Next chunk, please!!!!!')

    return final_stalkers_graph


def compute_most_stalking_people(data_folder, checkins_filename, edges_filename):
    """
    Answers the questions by calculating which stalker pair has the highest score
    for pairs of people who are friends to each other or not, as a tuple in that
    order
    """
    highest_friend_stalker = (None, 0)
    highest_nonfriend_stalker = (None, 0)

    graph_gen = read_stalkers_graph(data_folder, checkins_filename)

    friendship_graph = read_friendship_graph(data_folder, edges_filename)
    stalkers_graph = obtain_stalkers_graph(data_folder, checkins_filename, edges_filename, graph_gen)
    stalking_dict = stalkers_graph.weights

    print('Computing answers...')

    for pair_locations in stalking_dict.items():
        pair, locations = pair_locations
        stalking_score = len(locations)

        if stalking_score > highest_friend_stalker[1]:
            if pair[0] in friendship_graph.relations[pair[1]]:
                highest_friend_stalker = (pair, stalking_score)
            else:
                highest_nonfriend_stalker = (pair, stalking_score)

    return highest_friend_stalker, highest_nonfriend_stalker


if __name__ == '__main__':
#    print('Do you want to download the datasets?')
#    print('1. Yes, please download them for me')
#    print('2. No, I\'ll add the *.gz files manually into ./data/')
#    option = input()
#
#    if option == '1':
#        obtain_data_files(EDGES_URL)
#        obtain_data_files(CHECKINS_URL)
#
#    extract_data_files(f'{EDGES_COMP_FILE}')
#    extract_data_files(f'{CHECKINS_COMP_FILE}')

    print('Counting lines on the checkins file. One moment please...')
    checkins_lines = count_checkins_lines()
    print(f'{checkins_lines} lines found.')

    block_sizes = [checkins_lines // N_CHUNKS if x < N_CHUNKS
                   else checkins_lines // N_CHUNKS + checkins_lines % N_CHUNKS
                   for x in range(N_CHUNKS)]
    print(f'Will distribute work in chunks of the following sizes: {block_sizes}')

    print('Starting analysis! This might take a while')

    start_time = timer()
    most_stalking_friend, most_stalking_nonfriend = compute_most_stalking_people(DATA_FOLDER, CHECKINS_FILE, EDGES_FILE)
    end_time = timer()
 
    print(f'Finished! The process took {timedelta(seconds = end_time - start_time)} (HH:MM:SS)!\n')
 
    print('The most stalking pair of non-friends is')
    print(most_stalking_nonfriend)
    print('The most stalking pair of non-friends is')
    print(most_stalking_friend)
