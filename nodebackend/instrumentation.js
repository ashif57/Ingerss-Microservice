const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
const { OTLPMetricExporter } = require('@opentelemetry/exporter-metrics-otlp-http');
const { OTLPLogExporter } = require('@opentelemetry/exporter-logs-otlp-http');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');
const { LoggerProvider, BatchLogRecordProcessor } = require('@opentelemetry/sdk-logs');
const { logs } = require('@opentelemetry/api-logs');

const traceExporter = new OTLPTraceExporter({
  url: (process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4318') + '/v1/traces',
});

const metricExporter = new OTLPMetricExporter({
  url: (process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4318') + '/v1/metrics',
});

const logExporter = new OTLPLogExporter({
  url: (process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4318') + '/v1/logs',
});

const resource = new Resource({
  [SemanticResourceAttributes.SERVICE_NAME]: process.env.OTEL_SERVICE_NAME || 'nodebackend-service',
});

const loggerProvider = new LoggerProvider({ resource });
loggerProvider.addLogRecordProcessor(new BatchLogRecordProcessor(logExporter));
logs.setGlobalLoggerProvider(loggerProvider);

const sdk = new NodeSDK({
  resource: resource,
  traceExporter,
  metricReader: new (require('@opentelemetry/sdk-metrics').PeriodicExportingMetricReader)({
    exporter: metricExporter,
  }),
  instrumentations: [getNodeAutoInstrumentations()]
});

sdk.start();
