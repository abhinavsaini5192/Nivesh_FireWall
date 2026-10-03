/**
 * Background Message Router (Phase 13.1 & 13.2)
 *
 * Routes incoming extension messages to validated handlers.
 */

import {
  handleGetStatus,
  handleScanRequest,
  handleOpenNiveshApp,
  handleCaptureRequest,
  handleCheckSelection,
} from './handlers';
import type {
  ExtensionMessage,
  ExtensionResponse,
  GetStatusMessage,
  ScanRequestMessage,
  OpenNiveshAppMessage,
  CaptureRequestMessage,
  CheckSelectionMessage,
} from '../types/messages';

export async function routeExtensionMessage(
  message: ExtensionMessage
): Promise<ExtensionResponse> {
  if (!message || !message.type) {
    return {
      success: false,
      requestId: 'UNKNOWN',
      error: {
        code: 'INVALID_MESSAGE',
        message: 'Message payload must include a valid message type.',
      },
    };
  }

  switch (message.type) {
    case 'GET_STATUS':
      return await handleGetStatus(message as GetStatusMessage);

    case 'CHECK_SELECTION':
      return await handleCheckSelection(message as CheckSelectionMessage);

    case 'CAPTURE_REQUEST':
      return await handleCaptureRequest(message as CaptureRequestMessage);

    case 'SCAN_REQUEST':
      return await handleScanRequest(message as ScanRequestMessage);

    case 'OPEN_NIVESH_APP':
      return await handleOpenNiveshApp(message as OpenNiveshAppMessage);

    default:
      return {
        success: false,
        requestId: message.requestId || 'UNKNOWN',
        error: {
          code: 'UNSUPPORTED_MESSAGE_TYPE',
          message: `The message type '${message.type}' is not supported by the background router.`,
        },
      };
  }
}
