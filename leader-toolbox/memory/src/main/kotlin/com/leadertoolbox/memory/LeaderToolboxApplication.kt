package com.leadertoolbox.memory

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.context.properties.ConfigurationPropertiesScan
import org.springframework.boot.runApplication
import org.springframework.cache.annotation.EnableCaching
import org.springframework.data.jpa.repository.config.EnableJpaRepositories
import org.springframework.scheduling.annotation.EnableAsync
import org.springframework.transaction.annotation.EnableTransactionManagement

/**
 * Leader Toolbox Memory System
 *
 * A comprehensive memory system built with:
 * - PostgreSQL for structured data and relationships
 * - Elasticsearch for full-text and vector search
 * - all-MiniLM-L6-v2 embeddings for semantic search
 * - Kotlin/Spring Boot for the backend services
 */
@SpringBootApplication
@EnableJpaRepositories
@EnableTransactionManagement
@EnableCaching
@EnableAsync
@ConfigurationPropertiesScan
class LeaderToolboxApplication

fun main(args: Array<String>) {
    runApplication<LeaderToolboxApplication>(*args)
}