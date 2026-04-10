import React from 'react';
import FontAwesome from '@expo/vector-icons/FontAwesome';
import { Tabs } from 'expo-router';
import { Brand } from '@/constants/Colors';

function TabBarIcon(props: {
  name: React.ComponentProps<typeof FontAwesome>['name'];
  color: string;
}) {
  return <FontAwesome size={24} style={{ marginBottom: -3 }} {...props} />;
}

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Brand.accent,
        tabBarInactiveTintColor: Brand.tabInactive,
        tabBarStyle: {
          backgroundColor: Brand.white,
          borderTopColor: Brand.blushDark,
          borderTopWidth: 1,
          paddingBottom: 8,
          paddingTop: 8,
          height: 60,
        },
        headerStyle: {
          backgroundColor: Brand.blush,
        },
        headerTintColor: Brand.textDark,
        headerTitleStyle: {
          fontWeight: '700',
          fontSize: 18,
        },
      }}>
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          headerTitle: 'BOABFIT',
          headerTitleStyle: {
            fontWeight: '800',
            fontSize: 20,
            letterSpacing: 3,
          },
          tabBarIcon: ({ color }) => <TabBarIcon name="home" color={color} />,
        }}
      />
      <Tabs.Screen
        name="calendar"
        options={{
          title: 'Calendar',
          tabBarIcon: ({ color }) => <TabBarIcon name="calendar" color={color} />,
        }}
      />
      <Tabs.Screen
        name="library"
        options={{
          title: 'Library',
          tabBarIcon: ({ color }) => <TabBarIcon name="book" color={color} />,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color }) => <TabBarIcon name="user" color={color} />,
        }}
      />
    </Tabs>
  );
}
