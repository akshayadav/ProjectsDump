//
//  HomeView.swift
//  ShortcutOnWakeSample
//
//  Created by Akshay Yadav on 5/29/25.
//

import SwiftUI
import Cocoa

struct HomeView: View {
    let wakeObserver: WakeObserver
    var body: some View {
        VStack {
            Text("This App runs in the background and runs a shortcut when system wakes up")
            Text("Currently running shortcut name: 'Turn On Desk Lamp'")
        }
    }
}

#Preview {
    HomeView(wakeObserver: WakeObserver())
}
