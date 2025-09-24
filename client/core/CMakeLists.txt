add_subdirectory(networking)
add_subdirectory(work)

target_sources(${CLIENT}
    PRIVATE
        client_config.c
        common.c
)