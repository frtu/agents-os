# leader-control-center

> As leaders, we don't have time to only solve one task as a time.

## Overview

Leader Control Center is a **human-in-the-loop supervisory** UI for durable AI workflows, called `meta orchestration`.

It allows leaders to supervise, prioritize, unblock, approve, and inspect dozens of long-running AI executions without constantly context-switching between conversations.

### What we want to resolve?

> Running an task that takes minutes and often requires manual approval & clarification.

This application aims to provide a **high level view** of all the running tasks, allow you to switch between well defined user stories / cases that you define & create. It prevent interruption every time a loop ask for your attention.

## Application

### Concepts

- **Task**: Unit of work that is processed by an agent
- **User story** or **Case** : Minimum of spec to deliver an output combining one or multiple tasks.
- **Epic** or **Area**: an consistent Area of topic achieving a certain goal / outcome that contains User stories. 

Attention : constrain your **Epic scope** in an achievable time frame (*recommended <1 month*), containing reasonable user stories (*recommended <10*). It pushes you to **breakdown complex problems** to simpler ones & create **incremental achievements**.

### Design

Vertical drawers with Epic title. Click on it to edit, approve change when clicking on the button on the right. Create new button should create a new collapsible drawer. Vertical order can drag up & down.

Inside each drawer, create 4 columns with 

- To do
- In progress
- Blocked
- Completed

## Architecture

Frontend only provide the interactive tool but immediately persist the state to a backend service.

### Frontend technology

ReactJS application.

### Backend technology

Python service providing swagger like interaction (easy to test).
