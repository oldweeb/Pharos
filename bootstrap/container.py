import argparse
import logger
import yaml
from dacite import from_dict, Config
from dependency_injector import containers, providers
from loguru import logger
from models.configuration import Configuration, AccountsMode
from runner import RunnerFactory


class ApplicationContainer(containers.DeclarativeContainer):
    config_path = providers.Configuration()
    configuration = providers.Singleton(
        lambda path: from_dict(
            data_class=Configuration,
            data=yaml.safe_load(open(path)),
            config=Config(cast=[AccountsMode])
        ),
        config_path
    )
    logger = providers.Object(logger)
    swaps_settings = providers.DelegatedCallable(
        lambda configuration: configuration.settings.swaps,
        configuration
    )
    runner=providers.Factory(
        lambda configuration, logger: RunnerFactory(configuration, logger).create(),
        configuration, logger
    )

def bootstrap_container() -> ApplicationContainer:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--configurationYaml',
        type=str,
        required=False,
        default='./data/configuration.yaml',
        help='Path to YAML file with configuration'
    )
    args = parser.parse_args()

    application_container = ApplicationContainer()
    application_container.config_path.override(args.configurationYaml)
    return application_container

container = bootstrap_container()