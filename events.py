from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Type, TypeVar

class Event(ABC):
    pass


class Subscriber(ABC):
    @abstractmethod
    def handle_event(self, event: Event) -> None:
        pass


class Service:
    def __init__(self, response_type: Any):
        self.response_type = response_type


class Client(ABC):
    @abstractmethod
    def handle_service(self, service: Service) -> Any:
        pass


class ServiceResult(Enum):
    Success = 1
    Failure = 0

    
class EventError(Exception):
    pass

class DuplicateClientError(EventError):
    pass

class NoClientRegisteredError(EventError):
    pass

class InvalidResponseTypeError(EventError):
    pass


E = TypeVar('E', bound=Event)
S = TypeVar('S', bound=Service)


class EventManager:
    def __init__(self):
        self.subscribers: Dict[Type[E], List[Subscriber]] = {}
        self.clients: Dict[Type[S], Client] = {}

    def subscribe(self, event_type: Type[E], subscriber: Subscriber) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(subscriber)

    def client(self, service_type: Type[S], client: Client) -> None:
        if service_type in self.clients:
            raise DuplicateClientError(
                f'Cannot register {client} as client for {service_type} as there is already a registered client.'
            )
        self.clients[service_type] = client

    def publish(self, event: Event) -> None:
        for subscriber in self.subscribers.get(type(event), []):
            subscriber.handle_event(event)

    def service(self, service: Service) -> Any:
        if type(service) not in self.clients:
            raise NoClientRegisteredError(f'No client registered for service {service} of type {type(service)}.')
        client = self.clients[type(service)]
        response = client.handle_service(service)
        if not isinstance(response, service.response_type):
            raise InvalidResponseTypeError(f'Unexpected response type {type(response)}; for service {service} \
                with client {client}, expected type {service.response_type}.')
        return response
