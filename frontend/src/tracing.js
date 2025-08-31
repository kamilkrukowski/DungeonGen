import React from 'react';
import { trace, context, SpanStatusCode } from '@opentelemetry/api';
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { JaegerExporter } from '@opentelemetry/exporter-jaeger';
import { Resource } from '@opentelemetry/resources';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';

// Initialize OpenTelemetry tracer
export function initTracer() {
  // Create a resource
  const resource = new Resource({
    'service.name': 'dungeongen-frontend',
    'service.version': '1.0.0',
  });

  // Create a TracerProvider
  const provider = new WebTracerProvider({
    resource: resource,
  });

  // Create a JaegerExporter
  const jaegerExporter = new JaegerExporter({
    endpoint: 'http://localhost:14268/api/traces', // Jaeger collector endpoint
  });

  // Create a BatchSpanProcessor and add the exporter to the TracerProvider
  const processor = new BatchSpanProcessor(jaegerExporter);
  provider.addSpanProcessor(processor);

  // Register the TracerProvider
  provider.register();

  // Initialize instrumentations
  new DocumentLoadInstrumentation().setTracerProvider(provider);
  new UserInteractionInstrumentation().setTracerProvider(provider);
  new FetchInstrumentation().setTracerProvider(provider);

  return trace.getTracer('dungeongen-frontend');
}

// Simple trace decorator for React components
export function withTracing(operationName) {
  return function (WrappedComponent) {
    return function TracedComponent(props) {
      const tracer = trace.getTracer('dungeongen-frontend');

      React.useEffect(() => {
        const span = tracer.startSpan(operationName);
        span.setAttribute('component.name', WrappedComponent.name);
        span.setAttribute('operation.type', 'component_mount');

        return () => {
          span.setAttribute('operation.type', 'component_unmount');
          span.end();
        };
      }, []);

      return <WrappedComponent {...props} />;
    };
  };
}

// Utility function to trace async operations
export async function traceAsync(operationName, operation) {
  const tracer = trace.getTracer('dungeongen-frontend');
  const span = tracer.startSpan(operationName);

  try {
    const result = await operation();
    span.setStatus({ code: SpanStatusCode.OK });
    return result;
  } catch (error) {
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: error.message
    });
    span.recordException(error);
    throw error;
  } finally {
    span.end();
  }
}

// Utility function to trace fetch requests
export async function traceFetch(url, options = {}) {
  return traceAsync('fetch_request', async () => {
    const tracer = trace.getTracer('dungeongen-frontend');
    const span = tracer.startSpan('fetch_request');

    span.setAttribute('http.url', url);
    span.setAttribute('http.method', options.method || 'GET');

    try {
      const response = await fetch(url, options);
      span.setAttribute('http.status_code', response.status);
      span.setStatus({ code: SpanStatusCode.OK });
      return response;
    } catch (error) {
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message
      });
      span.recordException(error);
      throw error;
    } finally {
      span.end();
    }
  });
}

// Initialize tracer when the module is imported
export const tracer = initTracer();
