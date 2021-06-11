import logging

logging.getLogger().setLevel(logging.INFO)


def get_release(file):
    import json
    try:
        package_json = open(file)
        package_json_dict = json.loads(package_json.read())

        release = package_json_dict['release']
        return release
    except FileNotFoundError:
        logging.error("File: {} not found, Please verify the file path.".format(file))
        raise
    except JSONDecodeError:
        logging.error("File: {} is not a valid json, Please provide a valid json file.".format(file))
        raise


def check_if_release_is_valid(branch_release, master_release):
    return branch_release >= master_release
