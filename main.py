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


class Graph:
    """
    This class represents the relations between people
    """
    def __init__(self):
        """
        Constructor initializer
        """
        self.relations = {}
        self.weights = {}

    def add_relation(self, start_node, end_node):
        """
        Adds a relation between two nodes
        """
        if not self.relations.get(start_node):
            self.relations[start_node] = {end_node}
        else:
            self.relations[start_node].add(end_node)

    def add_weight(self, start_node, end_node, weight):
        """
        Adds a weight for a couple of nodes' association
        """
        pair = start_node, end_node
        if not self.weights.get(pair):
            self.weights[pair] = {weight}
        else:
            self.weights[pair].add(weight)

    def __str__(self):
        return f'Graph with nodes:\n{self.relations}\nAnd weights:\n{self.weights}'


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


def read_friendship_graph(friends_file):
    """
    Reads the edges (friendships) file and returns a graph with the associations
    """
    print('\tBuilding the Friendship Graph...')
    friendship_graph = Graph()

    with open(friends_file) as edges:
        for line in edges:
            user, friend = line.split('\t')
            user = int(user)
            friend = int(friend.replace('\n', ''))
            friendship_graph.add_relation(user, friend)

    print('\tFinished building the Friendship Graph')
    return friendship_graph


def read_stalkers_graph(checkins_file):
    """
    Reads the check-ins file and returns a graph with the associations between people
    that mean stalking (weighted as a list of involved location ids)
    """
    print('\tBuilding the Stalkers Graph')
    stalkers_graph = Graph()
    visit_records = {}
    i = 0

    with open(checkins_file) as checkins:
        for line in checkins:
            if i > 0 and i % 50000 == 0:
                print(f'\t\tProcessed {i} check-in records')

            user_id, checkin_time, _, _, location_id = line.split('\t')
            user_id = int(user_id)
            checkin_time = checkin_time.replace('Z', '+00:00')
            location_id = int(location_id.replace('\n', ''))

            new_visit = (user_id, checkin_time)

            if not visit_records.get(location_id):
                visit_records[location_id] = [new_visit]
            else:
                for visit in visit_records[location_id]:
                    if new_visit[1] < visit[1]:
                        stalkers_graph.add_weight(new_visit[0], visit[0], location_id)
                    else:
                        stalkers_graph.add_weight(visit[0], new_visit[0], location_id)
                
                visit_records[location_id].append(new_visit)
            i += 1

    print('\tFinished building the Stalkers Graph')
    return stalkers_graph


def compute_most_stalking_people(data_folder, checkins_filename, edges_filename):
    """
    Answers the questions by calculating which stalker pair has the highest score
    for pairs of people who are friends to each other or not, as a tuple in that
    order
    """
    highest_friend_stalker = (None, 0)
    highest_nonfriend_stalker = (None, 0)
    friendship_graph = read_friendship_graph(f'{data_folder}{edges_filename}')
    stalkers_graph = read_stalkers_graph(f'{data_folder}{checkins_filename}')
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
    print('Do you want to download the datasets?')
    print('1. Yes, please download them for me')
    print('2. No, I\'ll add the *.gz files manually into ./data/')
    option = input()

    if option == '1':
        obtain_data_files(EDGES_URL)
        obtain_data_files(CHECKINS_URL)

    extract_data_files(f'{EDGES_COMP_FILE}')
    extract_data_files(f'{CHECKINS_COMP_FILE}')

    print('Starting analysis! This might take a while')

    start_time = timer()
    most_stalking_friend, most_stalking_nonfriend = compute_most_stalking_people(DATA_FOLDER, CHECKINS_FILE, EDGES_FILE)
    end_time = timer()

    print(f'Finished! The process took {timedelta(seconds = end_time - start_time)} (HH:MM:SS)!\n')

    print('The most stalking pair of non-friends is')
    print(most_stalking_nonfriend)
    print('The most stalking pair of non-friends is')
    print(most_stalking_friend)
