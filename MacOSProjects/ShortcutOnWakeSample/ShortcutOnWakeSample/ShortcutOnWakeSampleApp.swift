//
//  ShortcutOnWakeSampleApp.swift
//  ShortcutOnWakeSample
//
//  Created by Akshay Yadav on 5/29/25.
//

import SwiftUI
import SwiftData

struct WebSocketConnectionFactoryEnvironmentKey: EnvironmentKey {
    static let defaultValue: WebSocketConnectionFactory = DefaultWebSocketConnectionFactory()
}

extension EnvironmentValues {
    var webSocketConnectionFactory: WebSocketConnectionFactory {
        get { self[WebSocketConnectionFactoryEnvironmentKey.self] }
        set { self[WebSocketConnectionFactoryEnvironmentKey.self] = newValue }
    }
}

@main
struct ShortcutOnWakeSampleApp: App {
    
    let wakeObserver = WakeObserver()
    var sharedModelContainer: ModelContainer = {
        let schema = Schema([
            Item.self,
        ])
        let modelConfiguration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)

        do {
            return try ModelContainer(for: schema, configurations: [modelConfiguration])
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }()

    var body: some Scene {
        WindowGroup {
            HomeView(wakeObserver: wakeObserver)
        }
        .modelContainer(sharedModelContainer)
    }
}
