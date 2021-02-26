import unittest
from main import Graph, read_friendship_graph, read_stalkers_graph
from main import compute_most_stalking_people, CHECKINS_FILE, EDGES_FILE

TEST_FOLDER = './test/'
TEST_EDGES_FILE = 'edgestest.txt'
TEST_CHECKINS_FILE = 'checkinstest.txt'


class SolutionTest(unittest.TestCase):
    """
    Class to execute unit tests of the solution from test cases at './test'
    """
    def setUp(self):
        """
        Unit test initialization
        """
        self.friends_graph = Graph()
        self.friends_graph.add_relation(1, 3)
        self.friends_graph.add_relation(2, 4)
        self.friends_graph.add_relation(3, 1)
        self.friends_graph.add_relation(4, 2)

        self.stalkers_graph = Graph()
        self.stalkers_graph.add_weight(1, 2, 1)
        self.stalkers_graph.add_weight(1, 2, 6)
        self.stalkers_graph.add_weight(1, 3, 2)
        self.stalkers_graph.add_weight(2, 3, 4)
        self.stalkers_graph.add_weight(2, 4, 3)
        self.stalkers_graph.add_weight(2, 1, 5)

        highest_stalker_friend = ((1, 3), 1)
        highest_stalker_nonfriend = ((1, 2), 2)
        self.highest_stalker_people = highest_stalker_friend, highest_stalker_nonfriend

    def tearDown(self):
        """
        Unit test clean-up
        """
        del(self.friends_graph)
        del(self.stalkers_graph)

    def test_read_friends_graph(self):
        """
        Test for the read_friendship_graph(...) method
        """
        computed_friends_graph = read_friendship_graph(f'{TEST_FOLDER}{TEST_EDGES_FILE}')
        self.assertEqual(self.friends_graph.relations, computed_friends_graph.relations)

    def test_read_stalkers_graph(self):
        """
        Test for the read_stalkers_graph(...) method
        """
        computed_stalkers_graph = read_stalkers_graph(f'{TEST_FOLDER}{TEST_CHECKINS_FILE}')
        self.assertEqual(self.stalkers_graph.weights, computed_stalkers_graph.weights)

    def test_compute_most_stalking_people(self):
        """
        Test for the compute_most_stalking_people() method
        """
        computed_highest_stalker_people = compute_most_stalking_people(CHECKINS_FILE, EDGES_FILE)
        self.assertEqual(self.highest_stalker_friend, computed_highest_stalker_people)


if __name__ == '__main__':
    unittest.main()