import argparse
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
    checkin_settings = providers.DelegatedCallable(
        lambda configuration: configuration.settings.checkin,
        configuration
    )
    faucet_settings = providers.DelegatedCallable(
        lambda configuration: configuration.settings.faucet,
        configuration
    )
    approval_service = providers.Singleton(lambda: __import__('services.approval_service', fromlist=['ApprovalService']).ApprovalService())
    balance_checker = providers.Singleton(lambda: __import__('services.balance_checker', fromlist=['BalanceChecker']).BalanceChecker())
    swaps = providers.Factory(
        lambda: __import__('features.swaps', fromlist=['Swaps']).Swaps(),
    )
    checkin = providers.Factory(
        lambda: __import__('features.checkin', fromlist=['CheckIn']).CheckIn(),
    )
    faucet = providers.Factory(
        lambda: __import__('features.faucet', fromlist=['Faucet']).Faucet(),
    )
    features = providers.List(
        faucet,
        checkin,
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