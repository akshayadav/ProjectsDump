import Foundation
import Network
import Darwin

// Simple TCP server using Network framework
// Usage: Pico2WMacServer [port]

let defaultPort: NWEndpoint.Port = NWEndpoint.Port(integerLiteral: 5005)
let port: NWEndpoint.Port = {
    if CommandLine.arguments.count > 1, let p = UInt16(CommandLine.arguments[1]) {
        return NWEndpoint.Port(rawValue: p) ?? defaultPort
    }
    return defaultPort
}()

let logFileName = "pico_temps.log"
let csvFileName = "pico_temps.csv"

let queue = DispatchQueue(label: "Pico2W.server.queue")

func appendLog(_ addr: NWEndpoint?, _ obj: Any) {
    let ts = ISO8601DateFormatter().string(from: Date())
    var addrStr = "?"
    if let endpoint = addr {
        addrStr = String(describing: endpoint)
    }
    let jsonStr: String
    if JSONSerialization.isValidJSONObject(obj) {
        if let d = try? JSONSerialization.data(withJSONObject: obj, options: []) {
            jsonStr = String(data: d, encoding: .utf8) ?? ""
        } else {
            jsonStr = "<unserializable>"
        }
    } else {
        jsonStr = String(describing: obj)
    }
    let line = "\(ts) - \(addrStr) - \(jsonStr)\n"
    let fileURL = URL(fileURLWithPath: FileManager.default.currentDirectoryPath).appendingPathComponent(logFileName)
    if let data = line.data(using: .utf8) {
        if FileManager.default.fileExists(atPath: fileURL.path) {
                    if let handle = try? FileHandle(forWritingTo: fileURL) {
                        defer { try? handle.close() }
                        do {
                            if #available(macOS 10.15.4, *) {
                                try handle.seekToEnd()
                                try handle.write(contentsOf: data)
                            } else {
                                // older APIs
                                handle.seekToEndOfFile()
                                handle.write(data)
                            }
                        } catch {
                            print("Log write error:", error)
                        }
            }
        } else {
            do {
                try data.write(to: fileURL)
            } catch {
                print("Log create error:", error)
            }
        }
    }
}

func appendCSV(_ addr: NWEndpoint?, _ obj: Any) {
    // CSV columns: timestamp, client, celsius, fahrenheit
    let ts = ISO8601DateFormatter().string(from: Date())
    var clientStr = "?"
    if let endpoint = addr {
        clientStr = String(describing: endpoint)
    }

    var celsiusVal: String = ""
    var fahrenheitVal: String = ""
    if let dict = obj as? [String: Any] {
        if let c = dict["celsius"] {
            celsiusVal = String(describing: c)
        }
        if let f = dict["fahrenheit"] {
            fahrenheitVal = String(describing: f)
        }
    }

    let csvLine = "\(ts),\(clientStr),\(celsiusVal),\(fahrenheitVal)\n"
    let fileURL = URL(fileURLWithPath: FileManager.default.currentDirectoryPath).appendingPathComponent(csvFileName)
    let header = "timestamp,client,celsius,fahrenheit\n"

    if !FileManager.default.fileExists(atPath: fileURL.path) {
        // create with header
        if let hdata = header.data(using: .utf8) {
            do { try hdata.write(to: fileURL) } catch { print("CSV create error:", error) }
        }
    }

    if let data = csvLine.data(using: .utf8) {
        if let handle = try? FileHandle(forWritingTo: fileURL) {
            defer { try? handle.close() }
            do {
                if #available(macOS 10.15.4, *) {
                    try handle.seekToEnd()
                    try handle.write(contentsOf: data)
                } else {
                    handle.seekToEndOfFile()
                    handle.write(data)
                }
            } catch {
                print("CSV write error:", error)
            }
        }
    }
}

func startListener(on port: NWEndpoint.Port) {
    let params = NWParameters.tcp
    let listener = try! NWListener(using: params, on: port)

    listener.newConnectionHandler = { (connection) in
        connection.start(queue: queue)
        handleConnection(connection)
    }

    listener.start(queue: queue)
    print("Listening on 0.0.0.0:\(port) (TCP)")
}

func printLocalAddresses() {
    var ifaddrPtr: UnsafeMutablePointer<ifaddrs>?
    guard getifaddrs(&ifaddrPtr) == 0, let firstAddr = ifaddrPtr else { return }
    print("Local network interfaces:")
    var ptr = firstAddr
    while true {
        let name = String(cString: ptr.pointee.ifa_name)
        if let addr = ptr.pointee.ifa_addr {
            let family = addr.pointee.sa_family
            if family == UInt8(AF_INET) {
                var addr4 = UnsafeRawPointer(addr).assumingMemoryBound(to: sockaddr_in.self).pointee
                var buffer = [CChar](repeating: 0, count: Int(INET_ADDRSTRLEN))
                var inaddr = addr4.sin_addr
                inet_ntop(AF_INET, &inaddr, &buffer, socklen_t(INET_ADDRSTRLEN))
                let ip = String(cString: buffer)
                print(" - \(name): \(ip)")
            } else if family == UInt8(AF_INET6) {
                var addr6 = UnsafeRawPointer(addr).assumingMemoryBound(to: sockaddr_in6.self).pointee
                var buffer = [CChar](repeating: 0, count: Int(INET6_ADDRSTRLEN))
                var in6 = addr6.sin6_addr
                inet_ntop(AF_INET6, &in6, &buffer, socklen_t(INET6_ADDRSTRLEN))
                let ip = String(cString: buffer)
                print(" - \(name): \(ip)")
            }
        }
        if let next = ptr.pointee.ifa_next {
            ptr = next
        } else {
            break
        }
    }
    freeifaddrs(ifaddrPtr)
}

func handleConnection(_ connection: NWConnection) {
    let remote = connection.endpoint
    print("Accepted connection from: \(String(describing: remote))")
    var buffer = Data()

    func receiveNext() {
        connection.receive(minimumIncompleteLength: 1, maximumLength: 4096) { (data, context, isComplete, error) in
            if let data = data, !data.isEmpty {
                buffer.append(data)
                // process lines
                while let range = buffer.firstRange(of: Data([0x0A])) { // newline
                    let lineData = buffer.subdata(in: 0..<range.lowerBound)
                    buffer.removeSubrange(0...range.lowerBound)
                    if let lineStr = String(data: lineData, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines), !lineStr.isEmpty {
                        processLine(lineStr, from: remote, on: connection)
                    }
                }
            }

            if isComplete || error != nil {
                print("Connection ended: \(String(describing: remote))")
                connection.cancel()
                return
            }
            // continue receiving
            receiveNext()
        }
    }

    receiveNext()
}

func processLine(_ line: String, from addr: NWEndpoint?, on connection: NWConnection) {
    // Try parse JSON
    let data = Data(line.utf8)
    do {
        let obj = try JSONSerialization.jsonObject(with: data, options: [])
        print("\(Date()) - \(String(describing: addr)) - \(obj)")
        appendLog(addr, obj)
        appendCSV(addr, obj)

        // send ack
        let ack: [String: Any] = ["status": "ok", "received": ISO8601DateFormatter().string(from: Date())]
        if let ackData = try? JSONSerialization.data(withJSONObject: ack, options: []) {
            var toSend = ackData
            toSend.append(0x0A) // newline
            connection.send(content: toSend, completion: .contentProcessed({ sendError in
                if let e = sendError {
                    print("ACK send error:", e)
                }
            }))
        }
    } catch {
        print("Non-JSON from \(String(describing: addr)): \(line)")
        // send error ack
        let errAck: [String: Any] = ["status": "error", "reason": "invalid_json"]
        if let ackData = try? JSONSerialization.data(withJSONObject: errAck, options: []) {
            var toSend = ackData
            toSend.append(0x0A)
            connection.send(content: toSend, completion: .contentProcessed({ _ in }))
        }
    }
}

// Start
startListener(on: port)

dispatchMain()
