import sys
from tests.tests import test_notification, test_automate

if __name__ == "__main__":
    if "--notify" in sys.argv:
        test_notification()
    elif "--automate" in sys.argv:
        test_automate()
    else:
        print("Usage: python test.py [--notify | --automate]")
    