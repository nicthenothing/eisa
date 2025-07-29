#!/bin/bash

# BSD 2-Clause License
# [License text same as original]

cp /mnt/dns/epc_zone /etc/bind
cp /mnt/dns/ims_zone /etc/bind
cp /mnt/dns/pub_3gpp_zone /etc/bind
cp /mnt/dns/e164.arpa /etc/bind
cp /mnt/dns/named.conf /etc/bind

# Function to generate domain name based on MNC length
generate_domain() {
    local mcc=$1
    local mnc=$2
    local domain_type=$3
    
    if [ ${#mnc} == 3 ]; then
        echo "${domain_type}.mnc${mnc}.mcc${mcc}.3gppnetwork.org"
    else
        echo "${domain_type}.mnc0${mnc}.mcc${mcc}.3gppnetwork.org"
    fi
}

# Generate primary domains
EPC_DOMAIN=$(generate_domain $MCC $MNC "epc")
IMS_DOMAIN=$(generate_domain $MCC $MNC "ims")
PUB_3GPP_DOMAIN=$(generate_domain $MCC $MNC "pub")

# Replace primary domain variables
sed -i 's|EPC_DOMAIN|'$EPC_DOMAIN'|g' /etc/bind/epc_zone
sed -i 's|DNS_IP|'$DNS_IP'|g' /etc/bind/epc_zone
[ -z "$PCRF_PUB_IP" ] && sed -i 's|PCRF_IP|'$PCRF_IP'|g' /etc/bind/epc_zone || sed -i 's|PCRF_IP|'$PCRF_PUB_IP'|g' /etc/bind/epc_zone
[ -z "$HSS_PUB_IP" ] && sed -i 's|HSS_IP|'$HSS_IP'|g' /etc/bind/epc_zone || sed -i 's|HSS_IP|'$HSS_PUB_IP'|g' /etc/bind/epc_zone

sed -i 's|IMS_DOMAIN|'$IMS_DOMAIN'|g' /etc/bind/ims_zone
sed -i 's|DNS_IP|'$DNS_IP'|g' /etc/bind/ims_zone
sed -i 's|PCSCF_IP|'$PCSCF_IP'|g' /etc/bind/ims_zone
sed -i 's|ICSCF_IP|'$ICSCF_IP'|g' /etc/bind/ims_zone
sed -i 's|SCSCF_IP|'$SCSCF_IP'|g' /etc/bind/ims_zone
sed -i 's|SMSC_IP|'$SMSC_IP'|g' /etc/bind/ims_zone

sed -i 's|PUB_3GPP_DOMAIN|'$PUB_3GPP_DOMAIN'|g' /etc/bind/pub_3gpp_zone
sed -i 's|DNS_IP|'$DNS_IP'|g' /etc/bind/pub_3gpp_zone
sed -i 's|ENTITLEMENT_SERVER_IP|'$ENTITLEMENT_SERVER_IP'|g' /etc/bind/pub_3gpp_zone

sed -i 's|IMS_DOMAIN|'$IMS_DOMAIN'|g' /etc/bind/e164.arpa
sed -i 's|DNS_IP|'$DNS_IP'|g' /etc/bind/e164.arpa

sed -i 's|EPC_DOMAIN|'$EPC_DOMAIN'|g' /etc/bind/named.conf
sed -i 's|IMS_DOMAIN|'$IMS_DOMAIN'|g' /etc/bind/named.conf
sed -i 's|PUB_3GPP_DOMAIN|'$PUB_3GPP_DOMAIN'|g' /etc/bind/named.conf

# Generate additional zones for supported PLMNs if multi-PLMN is enabled
if [ "$ENABLE_MULTI_PLMN" = "true" ] && [ -n "$SUPPORTED_PLMNS" ]; then
    echo "Generating multi-PLMN DNS zones..."
    
    IFS=',' read -ra PLMN_ARRAY <<< "$SUPPORTED_PLMNS"
    for plmn in "${PLMN_ARRAY[@]}"; do
        IFS=':' read -ra PLMN_PARTS <<< "$plmn"
        plmn_mcc="${PLMN_PARTS[0]}"
        plmn_mnc="${PLMN_PARTS[1]}"
        
        # Skip if it's the primary PLMN
        if [ "$plmn_mcc" = "$MCC" ] && [ "$plmn_mnc" = "$MNC" ]; then
            continue
        fi
        
        # Generate domains for this PLMN
        plmn_epc_domain=$(generate_domain $plmn_mcc $plmn_mnc "epc")
        plmn_ims_domain=$(generate_domain $plmn_mcc $plmn_mnc "ims")
        plmn_pub_domain=$(generate_domain $plmn_mcc $plmn_mnc "pub")
        
        # Create zone files for this PLMN
        cp /etc/bind/epc_zone /etc/bind/epc_zone_${plmn_mcc}_${plmn_mnc}
        cp /etc/bind/ims_zone /etc/bind/ims_zone_${plmn_mcc}_${plmn_mnc}
        cp /etc/bind/pub_3gpp_zone /etc/bind/pub_3gpp_zone_${plmn_mcc}_${plmn_mnc}
        
        # Update zone files with PLMN-specific domains
        sed -i "s|$EPC_DOMAIN|$plmn_epc_domain|g" /etc/bind/epc_zone_${plmn_mcc}_${plmn_mnc}
        sed -i "s|$IMS_DOMAIN|$plmn_ims_domain|g" /etc/bind/ims_zone_${plmn_mcc}_${plmn_mnc}
        sed -i "s|$PUB_3GPP_DOMAIN|$plmn_pub_domain|g" /etc/bind/pub_3gpp_zone_${plmn_mcc}_${plmn_mnc}
        
        # Add zones to named.conf
        cat >> /etc/bind/named.conf << EOF

zone "$plmn_epc_domain" {
    type master;
    file "/etc/bind/epc_zone_${plmn_mcc}_${plmn_mnc}";
};

zone "$plmn_ims_domain" {
    type master;
    file "/etc/bind/ims_zone_${plmn_mcc}_${plmn_mnc}";
};

zone "$plmn_pub_domain" {
    type master;
    file "/etc/bind/pub_3gpp_zone_${plmn_mcc}_${plmn_mnc}";
};
EOF
        
        echo "Generated DNS zones for PLMN ${plmn_mcc}:${plmn_mnc}"
    done
fi

# Sync docker time
#ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone