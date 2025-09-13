add_subdirectory(networking)

target_sources(${CLIENT}
    PRIVATE
        client_config.c
        common.c
)