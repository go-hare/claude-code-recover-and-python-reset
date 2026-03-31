export type ConnectorTextBlock = {
  type: 'connector_text'
  connector_text: string
}

export type ConnectorTextDelta = {
  type: 'connector_text_delta'
  connector_text: string
}

export function isConnectorTextBlock(
  value: unknown,
): value is ConnectorTextBlock {
  return Boolean(
    value &&
      typeof value === 'object' &&
      (value as { type?: unknown }).type === 'connector_text' &&
      typeof (value as { connector_text?: unknown }).connector_text === 'string',
  )
}
