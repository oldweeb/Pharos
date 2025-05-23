import argparse
import yaml
from dacite import from_dict, Config
from dependency_injector import containers, providers
from loguru import logger
from models.configuration import Configuration, AccountsMode
from runner import RunnerFactory
from services.balance_checker import BalanceChecker


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
    balance_checker = providers.Singleton(lambda: BalanceChecker())
    swaps = providers.Factory(
        lambda balance_checker, settings, logger: __import__('features.swaps', fromlist=['Swaps']).Swaps(),
        balance_checker, swaps_settings, logger
    )
    features = providers.List(
        swaps
    )
    runner = providers.Factory(
        lambda features, configuration, logger: RunnerFactory(features, configuration, logger).create(),
        features, configuration, logger
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