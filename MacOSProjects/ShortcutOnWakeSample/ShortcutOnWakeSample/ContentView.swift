//
//  ContentView.swift
//  ShortcutOnWakeSample
//
//  Created by Akshay Yadav on 5/29/25.
//

import SwiftUI
import SwiftData
import IOKit

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    @Query private var items: [Item]
    
    
    
    @State
    var selection: Item?

    var body: some View {
        NavigationSplitView {
            List(selection: $selection) {
                ForEach(items, id: \.self) { item in
                    NavigationLink {
                        Text("Item at \(item.timestamp, format: Date.FormatStyle(date: .numeric, time: .standard))")
                    } label: {
                        Text(item.timestamp, format: Date.FormatStyle(date: .numeric, time: .standard))
                    }
                }
                }
                .onDeleteCommand {
                    if let selected = selection, let index = items.firstIndex(where: { elem in
                        elem.id == selected.id
                    }) {
                        
                        deleteItem(index: index)
                        selection = nil
                    }
                }
            
            .navigationSplitViewColumnWidth(min: 180, ideal: 200)
            .toolbar {
                ToolbarItem {
                    Button(action: addItem) {
                        Label("Add Item", systemImage: "plus")
                    }
                }
            }
        } detail: {
            Text("Select an item")
        }
    }

    private func addItem() {
        withAnimation {
            let newItem = Item(timestamp: Date())
            modelContext.insert(newItem)
        }
    }

    private func deleteItems(offsets: IndexSet) {
        withAnimation {
            for index in offsets {
                modelContext.delete(items[index])
            }
        }
    }
    
    private func deleteItem(index: Int) {
        withAnimation {
            modelContext.delete(items[index])
        }
    }
}

#Preview {
    ContentView()
        .modelContainer(for: Item.self, inMemory: true)
}
