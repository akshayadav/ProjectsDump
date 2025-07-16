//
//  PIRServerListener.swift
//  ShortcutOnWakeSample
//
//  Created by Akshay Yadav on 7/2/25.
//

import Foundation

//class WebSocketListener: NSObject, URLSessionWebSocketDelegate {
//    
//    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didOpenWithProtocol protocol: String?) {
//        
//    }
//    
//    func urlSession(_ session: URLSession, webSocketTask: URLSessionWebSocketTask, didCloseWith closeCode: URLSessionWebSocketTask.CloseCode, reason: Data?) {
//        
//    }
//    
//}

/// Enumeration of possible errors that might occur while using ``WebSocketConnection``.
public enum WebSocketConnectionError: Error {
    case connectionError
    case transportError
    case encodingError
    case decodingError
    case disconnected
    case closed
}


public final class WebSocketConnection: NSObject, Sendable {
    private let webSocketTask: URLSessionWebSocketTask

    internal init(
        webSocketTask: URLSessionWebSocketTask,
        encoder: JSONEncoder = JSONEncoder(),
        decoder: JSONDecoder = JSONDecoder()
    ) {
        self.webSocketTask = webSocketTask

        super.init()

        webSocketTask.resume()
    }

    deinit {
        // Make sure to cancel the WebSocketTask (if not already canceled or completed)
        webSocketTask.cancel(with: .goingAway, reason: nil)
    }

    private func receiveSingleMessage() async throws -> String {
        switch try await webSocketTask.receive() {
            case let .data(messageData):
                guard let message = String(data: messageData, encoding: .utf8) else {
                    throw WebSocketConnectionError.decodingError
                }

                return message

            case let .string(text):
    
                return text

            @unknown default:
                assertionFailure("Unknown message type")

                // Unsupported data, closing the WebSocket Connection
                webSocketTask.cancel(with: .unsupportedData, reason: nil)
                throw WebSocketConnectionError.decodingError
        }
    }
}

// MARK: Public Interface

extension WebSocketConnection {
    func send(_ message: String) async throws {
        guard let messageData = try? JSONEncoder().encode(message) else {
            throw WebSocketConnectionError.encodingError
        }

        do {
            try await webSocketTask.send(.data(messageData))
        } catch {
            switch webSocketTask.closeCode {
                case .invalid:
                    throw WebSocketConnectionError.connectionError

                case .goingAway:
                    throw WebSocketConnectionError.disconnected

                case .normalClosure:
                    throw WebSocketConnectionError.closed

                default:
                    throw WebSocketConnectionError.transportError
            }
        }
    }

    func receiveOnce() async throws -> String {
        do {
            return try await receiveSingleMessage()
        } catch let error as WebSocketConnectionError {
            throw error
        } catch {
            switch webSocketTask.closeCode {
                case .invalid:
                    throw WebSocketConnectionError.connectionError

                case .goingAway:
                    throw WebSocketConnectionError.disconnected

                case .normalClosure:
                    throw WebSocketConnectionError.closed

                default:
                    throw WebSocketConnectionError.transportError
            }
        }
    }

    func receive() -> AsyncThrowingStream<String, Error> {
        AsyncThrowingStream { [weak self] in
            guard let self else {
                // Self is gone, return nil to end the stream
                return nil
            }

            let message = try await self.receiveOnce()

            // End the stream (by returning nil) if the calling Task was canceled
            return Task.isCancelled ? nil : message
        }
    }

    func close() {
        webSocketTask.cancel(with: .normalClosure, reason: nil)
    }
}
