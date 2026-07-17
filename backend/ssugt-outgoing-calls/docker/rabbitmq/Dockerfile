FROM rabbitmq:4.1.2-management

ADD https://github.com/rabbitmq/rabbitmq-delayed-message-exchange/releases/download/v4.1.0/rabbitmq_delayed_message_exchange-4.1.0.ez /plugins/

RUN rabbitmq-plugins enable --offline rabbitmq_delayed_message_exchange