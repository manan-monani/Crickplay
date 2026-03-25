-- Fact: Delivery
-- One row per ball bowled — the most granular fact table
-- Contains foreign keys to all dimensions and core measures

{{
    config(
        materialized='incremental',
        schema='gold',
        unique_key='delivery_sk',
        on_schema_change='append_new_columns'
    )
}}


with deliveries as (
    select * from {{ ref('stg_deliveries') }}

    {% if is_incremental() %}
    where ingested_at > (select max(loaded_at) from {{ this }})
    {% endif %}
),

-- Join with dimension keys
enriched as (
    select
        -- Surrogate key for this delivery
        {{ dbt_utils.generate_surrogate_key([
            'd.match_id',
            'd.innings_number',
            'd.over_number',
            'd.ball_number'
        ]) }} as delivery_sk,

        -- Natural key
        d.delivery_id,
        d.match_id,

        -- Dimension foreign keys
        dp_batter.player_sk as batter_key,
        dp_bowler.player_sk as bowler_key,
        dv.venue_sk as venue_key,
        d.match_date::date as date_key,

        -- Innings position
        d.innings_number,
        d.over_number,
        d.ball_number,

        -- Players (denormalized for convenience)
        d.batter,
        d.bowler,
        d.non_striker,

        -- Teams
        d.batting_team,
        d.bowling_team,

        -- Core measures
        d.batter_runs,
        d.extra_runs,
        d.total_runs,
        d.extras_type,

        -- Boolean flags
        d.is_wicket,
        d.is_legal_delivery,
        case when d.batter_runs = 4 then true else false end as is_four,
        case when d.batter_runs = 6 then true else false end as is_six,
        case when d.batter_runs in (4, 6) then true else false end as is_boundary,
        case when d.total_runs = 0 then true else false end as is_dot_ball,

        -- Wicket details
        d.wicket_kind,
        d.wicket_player_out,

        -- Match outcome (for ML target variable)
        d.match_winner,

        -- Win probability delta (populated by ML pipeline later)
        null::float as win_probability_delta,

        -- Multi-tenancy
        'default' as tenant_id,

        -- Metadata
        d.ingested_at,
        current_timestamp as loaded_at

    from deliveries d
    left join {{ ref('dim_player') }} dp_batter
        on d.batter = dp_batter.player_name
    left join {{ ref('dim_player') }} dp_bowler
        on d.bowler = dp_bowler.player_name
    left join {{ ref('dim_venue') }} dv
        on d.venue = dv.stadium_name
)

select * from enriched
